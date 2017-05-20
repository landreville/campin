import { BrowserModule } from "@angular/platform-browser";
import { FormsModule } from "@angular/forms";
import { HttpModule } from "@angular/http";
import { ApplicationRef, NgModule } from "@angular/core";
import { createInputTransfer, createNewHosts, removeNgStyles } from "@angularclass/hmr";
import { PreloadAllModules, RouterModule } from "@angular/router";
// Imports for loading & configuring the in-memory web api
// import {InMemoryWebApiModule} from 'angular-in-memory-web-api';
// import {InMemoryDataService}  from './in-memory-data.service';
import { Ng2PageScrollModule } from "ng2-page-scroll";
import { ENV_PROVIDERS } from "./environment";
import { ROUTES } from "./app.routes";
import { AppComponent } from "./app.component";
import { APP_RESOLVER_PROVIDERS } from "./app.resolver";
import { AppState, InternalStateType } from "./app.service";
import { SearchComponent } from "./search";
import { PlaceAutocompleteComponent } from "./place-autocomplete";
import { MyDatePickerModule } from "mydatepicker";
import { AfterValidatorDirective } from "./validators/validate-after.directive";
import { FreeParksComponent } from "./freeparks";
import { SearchService } from "./services";
import { NoOpComponent } from "./noop.component";
import { CampSitesComponent } from "./campsites";
import { SitePanelComponent } from "./site-panel";
import { ShowboxComponent } from "./showbox";
import { MapItems } from "./map-items";
import { RangeSliderComponent } from "./range-slider";
import { CampSitesFilterComponent } from "./campsites-filter";

import "../styles/styles.scss";
import "../styles/headings.css";

// Application wide providers
const APP_PROVIDERS = [
    ...APP_RESOLVER_PROVIDERS,
    AppState
];

type StoreType = {
    state: InternalStateType,
    restoreInputValues: () => void,
    disposeOldHosts: () => void
};

/**
 * `AppModule` is the main entry point into Angular2's bootstraping process
 */
@NgModule({
    bootstrap: [AppComponent],
    declarations: [
        AppComponent,
        SearchComponent,
        PlaceAutocompleteComponent,
        AfterValidatorDirective,
        FreeParksComponent,
        NoOpComponent,
        CampSitesComponent,
        SitePanelComponent,
        MapItems,
        ShowboxComponent,
        RangeSliderComponent,
        CampSitesFilterComponent
    ],
    imports: [
        BrowserModule,
        FormsModule,
        HttpModule,
        RouterModule.forRoot(ROUTES, {
            useHash: true,
            preloadingStrategy: PreloadAllModules
        }),
        MyDatePickerModule,
        // InMemoryWebApiModule.forRoot(InMemoryDataService),
        Ng2PageScrollModule.forRoot()
    ],
    providers: [
        ENV_PROVIDERS,
        APP_PROVIDERS,
        SearchService
    ]
})
export class AppModule {

    constructor(public appRef: ApplicationRef,
                public appState: AppState) {
    }

    public hmrOnInit(store: StoreType) {
        if (!store || !store.state) {
            return;
        }

        // set state
        this.appState._state = store.state;
        // set input values
        if ('restoreInputValues' in store) {
            let restoreInputValues = store.restoreInputValues;
            setTimeout(restoreInputValues);
        }

        this.appRef.tick();
        delete store.state;
        delete store.restoreInputValues;
    }

    public hmrOnDestroy(store: StoreType) {
        const cmpLocation = this.appRef.components.map((cmp) => cmp.location.nativeElement);
        // save state
        const state = this.appState._state;
        store.state = state;
        // recreate root elements
        store.disposeOldHosts = createNewHosts(cmpLocation);
        // save input values
        store.restoreInputValues = createInputTransfer();
        // remove styles
        removeNgStyles();
    }

    public hmrAfterDestroy(store: StoreType) {
        // display new elements
        store.disposeOldHosts();
        delete store.disposeOldHosts;
    }

}
